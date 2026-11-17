<?php
// Exécuté une seule fois, à la première installation.
// L'image Dolibarr enregistre le mot de passe administrateur initial en MD5 (faible) :
// on active le hachage moderne (password_hash / bcrypt) et on ré-enregistre le mot de passe.
chdir('/var/www/html');
require_once '/var/www/html/master.inc.php';
require_once DOL_DOCUMENT_ROOT.'/core/lib/admin.lib.php';
require_once DOL_DOCUMENT_ROOT.'/user/class/user.class.php';

dolibarr_set_const($db, 'MAIN_SECURITY_HASH_ALGO', 'password_hash', 'chaine', 0, '', 0);
$conf->global->MAIN_SECURITY_HASH_ALGO = 'password_hash';

$admin = new User($db);
if ($admin->fetch(0, getenv('DOLI_ADMIN_LOGIN')) > 0) {
	$res = $admin->setPassword($admin, getenv('DOLI_ADMIN_PASSWORD'), 0, 1);
	print($res === getenv('DOLI_ADMIN_PASSWORD') || $res > 0 ? "[securite] Mot de passe admin re-haché (bcrypt)\n"
		: "[securite] ECHEC du re-hachage du mot de passe admin\n");
} else {
	print("[securite] Administrateur introuvable\n");
}
