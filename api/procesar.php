<?php

declare(strict_types=1);

require_once __DIR__ . '/auth.php';
require_once __DIR__ . '/db.php';

header('Content-Type: application/json');
require_auth();

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode([
        'ok' => false,
        'error' => 'Metodo no permitido'
    ]);
    exit;
}

$rawBody = file_get_contents('php://input');
$payload = json_decode($rawBody ?: '{}', true);
if (!is_array($payload)) {
    $payload = [];
}

$rowid = isset($payload['rowid']) ? (int)$payload['rowid'] : 0;
if ($rowid <= 0) {
    http_response_code(400);
    echo json_encode([
        'ok' => false,
        'error' => 'Campo rowid es requerido y debe ser mayor a 0'
    ]);
    exit;
}

try {
    $pdo = get_connection();
    $pdo->beginTransaction();

    $selectSql = <<<'SQL'
        SELECT
            rowid,
            destiny_bank_reference,
            origin_bank_code,
            client_id,
            client_phone,
            amount,
            procesado
        FROM public.llx_bnc_push_notificaciones
        WHERE rowid = :rowid
        FOR UPDATE
    SQL;

    $selectStmt = $pdo->prepare($selectSql);
    $selectStmt->execute([':rowid' => $rowid]);
    $row = $selectStmt->fetch();

    if (!$row) {
        $pdo->rollBack();
        http_response_code(404);
        echo json_encode([
            'ok' => false,
            'error' => 'Registro no encontrado'
        ]);
        exit;
    }

    if ($row['procesado'] === true || $row['procesado'] === 't' || $row['procesado'] === 1 || $row['procesado'] === '1') {
        $pdo->commit();
        echo json_encode([
            'ok' => true,
            'updated' => false,
            'message' => 'El registro ya estaba procesado',
            'data' => [
                'rowid' => (int)$row['rowid'],
                'destiny_bank_reference' => $row['destiny_bank_reference'],
                'origin_bank_code' => $row['origin_bank_code'],
                'client_id' => $row['client_id'],
                'client_phone' => $row['client_phone'],
                'amount' => $row['amount']
            ]
        ]);
        exit;
    }

    $updateSql = <<<'SQL'
        UPDATE public.llx_bnc_push_notificaciones
        SET procesado = true
        WHERE rowid = :rowid
    SQL;

    $updateStmt = $pdo->prepare($updateSql);
    $updateStmt->execute([':rowid' => $rowid]);

    $pdo->commit();

    echo json_encode([
        'ok' => true,
        'updated' => true,
        'message' => 'Registro procesado correctamente',
        'data' => [
            'rowid' => (int)$row['rowid'],
            'destiny_bank_reference' => $row['destiny_bank_reference'],
            'origin_bank_code' => $row['origin_bank_code'],
            'client_id' => $row['client_id'],
            'client_phone' => $row['client_phone'],
            'amount' => $row['amount']
        ]
    ]);
} catch (Throwable $ex) {
    if (isset($pdo) && $pdo->inTransaction()) {
        $pdo->rollBack();
    }

    http_response_code(500);
    echo json_encode([
        'ok' => false,
        'error' => 'Error procesando registro',
        'details' => $ex->getMessage()
    ]);
}
