<?php

declare(strict_types=1);

require_once __DIR__ . '/config.php';

function get_connection(): PDO
{
    $host = env_value('DB_HOST', '127.0.0.1');
    $port = env_value('DB_PORT', '5432');
    $dbName = env_value('DB_NAME');
    $user = env_value('DB_USER');
    $pass = env_value('DB_PASS');

    if ($dbName === null || $user === null || $pass === null) {
        throw new RuntimeException('Faltan variables de entorno de base de datos');
    }

    $dsn = sprintf('pgsql:host=%s;port=%s;dbname=%s', $host, $port, $dbName);
    $pdo = new PDO($dsn, $user, $pass, [
        PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
        PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
        PDO::ATTR_EMULATE_PREPARES => false,
    ]);

    return $pdo;
}
