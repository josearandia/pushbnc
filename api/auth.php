<?php

declare(strict_types=1);

require_once __DIR__ . '/config.php';

function get_bearer_token(): ?string
{
    $authHeader = $_SERVER['HTTP_AUTHORIZATION'] ?? null;
    if ($authHeader === null && function_exists('getallheaders')) {
        $headers = getallheaders();
        $authHeader = $headers['Authorization'] ?? $headers['authorization'] ?? null;
    }

    if ($authHeader === null) {
        return null;
    }

    if (!preg_match('/^Bearer\\s+(.*)$/i', $authHeader, $matches)) {
        return null;
    }

    return trim($matches[1]);
}

function require_auth(): void
{
    $expectedToken = env_value('API_BEARER_TOKEN');
    $providedToken = get_bearer_token();

    if ($expectedToken === null || $expectedToken === '') {
        http_response_code(500);
        header('Content-Type: application/json');
        echo json_encode([
            'ok' => false,
            'error' => 'API_BEARER_TOKEN no configurado en el servidor'
        ]);
        exit;
    }

    if ($providedToken === null || !hash_equals($expectedToken, $providedToken)) {
        http_response_code(401);
        header('Content-Type: application/json');
        echo json_encode([
            'ok' => false,
            'error' => 'No autorizado'
        ]);
        exit;
    }
}
