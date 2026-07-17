<?php

declare(strict_types=1);

require_once __DIR__ . '/auth.php';
require_once __DIR__ . '/db.php';

header('Content-Type: application/json');
require_auth();

if ($_SERVER['REQUEST_METHOD'] !== 'GET') {
    http_response_code(405);
    echo json_encode([
        'ok' => false,
        'error' => 'Metodo no permitido'
    ]);
    exit;
}

$cedula = trim($_GET['cedula'] ?? '');
if ($cedula === '') {
    http_response_code(400);
    echo json_encode([
        'ok' => false,
        'error' => 'Parametro cedula es requerido'
    ]);
    exit;
}

try {
    $pdo = get_connection();

    $sql = <<<'SQL'
        SELECT
            rowid,
            destiny_bank_reference,
            origin_bank_code,
            client_id,
            client_phone,
            amount,
            tx_date,
            tx_hour,
            payment_type,
            fecha_registro
        FROM public.llx_bnc_push_notificaciones
        WHERE client_id = :cedula
          AND procesado = false
        ORDER BY fecha_registro DESC, rowid DESC
    SQL;

    $stmt = $pdo->prepare($sql);
    $stmt->execute([':cedula' => $cedula]);

    $rows = $stmt->fetchAll();

    echo json_encode([
        'ok' => true,
        'count' => count($rows),
        'data' => $rows
    ]);
} catch (Throwable $ex) {
    http_response_code(500);
    echo json_encode([
        'ok' => false,
        'error' => 'Error consultando notificaciones',
        'details' => $ex->getMessage()
    ]);
}
