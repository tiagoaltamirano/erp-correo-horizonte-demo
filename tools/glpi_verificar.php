<?php
require '/var/www/glpi/vendor/autoload.php';
$kernel = new \Glpi\Kernel\Kernel();
$kernel->boot();
$usuario = new User();
if (!$usuario->getFromDBbyName('glpi') || !password_verify(getenv('DEMO_PASSWORD'), $usuario->fields['password'])) {
    throw new RuntimeException('La credencial local de GLPI no coincide con su configuración');
}
$categoria = new ITILCategory();
$filas = $categoria->find(['name'=>'ERP Correo Horizonte']);
if (count($filas)!==1 || (int)reset($filas)['users_id'] !== (int)$usuario->getID()) {
    throw new RuntimeException('La categoría o el técnico de GLPI no están preparados');
}
echo "GLPI: credencial, categoría y técnico preparados y conservados.\n";
