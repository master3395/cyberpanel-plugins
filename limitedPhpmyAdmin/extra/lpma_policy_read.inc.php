<?php
/**
 * Install: copy to /usr/local/CyberCP/plogical/lpma_policy_read.inc.php
 * (included by phpmyadminsignin.php and public/phpmyadmin/index.php)
 */
function lpma_read_limited_policy(): array
{
    $defaultBlocked = [
        'manage' => true,
        'two_factor' => true,
        'features' => true,
        'sql' => true,
        'navigation' => true,
        'main_panel' => true,
        'export' => true,
        'import' => true,
    ];
    $policy = [
        'strict_mode' => true,
        'blocked_tabs' => $defaultBlocked,
    ];
    $paths = [
        '/usr/local/CyberCP/pluginState/limited_phpmyadmin_policy.json',
        '/var/lib/cyberpanel-panelstate/limited_phpmyadmin_policy.json',
        '/etc/cyberpanel/limited_phpmyadmin_policy.json',
    ];
    foreach ($paths as $policyPath) {
        if (! @is_readable($policyPath)) {
            continue;
        }
        $raw = @file_get_contents($policyPath);
        if ($raw === false) {
            continue;
        }
        $decoded = @json_decode($raw, true);
        if (! is_array($decoded)) {
            continue;
        }
        $policy['strict_mode'] = isset($decoded['strict_mode']) ? (bool) $decoded['strict_mode'] : true;
        if (isset($decoded['blocked_tabs']) && is_array($decoded['blocked_tabs'])) {
            foreach ($defaultBlocked as $k => $_v) {
                $policy['blocked_tabs'][$k] = isset($decoded['blocked_tabs'][$k])
                    ? (bool) $decoded['blocked_tabs'][$k]
                    : true;
            }
        }
        break;
    }

    return $policy;
}
