<?php
/**
 * Mautic Configuration Updater
 * Safely updates Mautic configuration without sed escaping issues
 */

if ($argc < 2) {
    echo "Usage: php update-config.php <config_file> [options]\n";
    echo "Options:\n";
    echo "  --mailer-dsn=<dsn>           Set mailer DSN\n";
    echo "  --mailer-from-name=<name>    Set mailer from name\n";
    echo "  --mailer-from-email=<email>  Set mailer from email\n";
    echo "  --api-rate-limiter-cache=<value>  Set API rate limiter cache (null, redis, etc.)\n";
    exit(1);
}

$configFile = $argv[1];
$options = [];

// Parse command line options
for ($i = 2; $i < $argc; $i++) {
    if (strpos($argv[$i], '--') === 0) {
        $parts = explode('=', $argv[$i], 2);
        if (count($parts) === 2) {
            $options[substr($parts[0], 2)] = $parts[1];
        }
    }
}

if (!file_exists($configFile)) {
    echo "Error: Configuration file not found: $configFile\n";
    exit(1);
}

// Load the configuration
$config = include $configFile;

if (!is_array($config)) {
    echo "Error: Invalid configuration file format\n";
    exit(1);
}

$changes = [];

// Update mailer configuration
if (isset($options['mailer-dsn'])) {
    $config['mailer_dsn'] = $options['mailer-dsn'];
    $changes[] = "mailer_dsn";
}

if (isset($options['mailer-from-name'])) {
    $config['mailer_from_name'] = $options['mailer-from-name'];
    $changes[] = "mailer_from_name";
}

if (isset($options['mailer-from-email'])) {
    $config['mailer_from_email'] = $options['mailer-from-email'];
    $changes[] = "mailer_from_email";
}

// Update API configuration
if (isset($options['api-rate-limiter-cache'])) {
    $config['api_rate_limiter_cache'] = $options['api-rate-limiter-cache'] === 'null' ? null : $options['api-rate-limiter-cache'];
    $changes[] = "api_rate_limiter_cache";
}

// Generate the updated configuration
$output = "<?php\n\nreturn [\n";

foreach ($config as $key => $value) {
    $indent = "    ";
    if (is_string($value)) {
        $output .= $indent . "'$key' => '$value',\n";
    } elseif (is_bool($value)) {
        $output .= $indent . "'$key' => " . ($value ? 'true' : 'false') . ",\n";
    } elseif (is_null($value)) {
        $output .= $indent . "'$key' => null,\n";
    } elseif (is_array($value)) {
        $output .= $indent . "'$key' => " . var_export($value, true) . ",\n";
    } else {
        $output .= $indent . "'$key' => $value,\n";
    }
}

$output .= "];\n";

// Write the updated configuration
if (file_put_contents($configFile, $output) === false) {
    echo "Error: Failed to write configuration file\n";
    exit(1);
}

echo "Configuration updated successfully. Changed: " . implode(', ', $changes) . "\n";
?> 