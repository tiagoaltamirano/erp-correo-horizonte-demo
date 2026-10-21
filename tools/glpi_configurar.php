<?php
// Configuración inicial idempotente de una instancia local de demostración.
require '/var/www/glpi/vendor/autoload.php';
$kernel = new \Glpi\Kernel\Kernel();
$kernel->boot();
$usuario = new User();
if (!$usuario->getFromDBbyName('glpi')) { throw new RuntimeException('Usuario inicial no disponible'); }
$id = $usuario->getID();
$_SESSION['glpiID'] = $id;
$_SESSION['glpi_currenttime'] = date('Y-m-d H:i:s');
$password = getenv('DEMO_PASSWORD');
if (!$password || strlen($password)<12) { throw new RuntimeException('Falta la contraseña local'); }
if (!$usuario->update(['id'=>$id,'password'=>$password,'password2'=>$password,'language'=>'es_AR','firstname'=>'Equipo','realname'=>'TI Correo Horizonte'])) {
    throw new RuntimeException('No se pudo preparar el usuario local');
}
$categoria = new ITILCategory();
$existente = $categoria->find(['name'=>'ERP Correo Horizonte']);
if (!$existente) {
    $categoria->add(['name'=>'ERP Correo Horizonte','entities_id'=>0,'is_recursive'=>1,'users_id'=>$id,'is_incident'=>1,'is_request'=>1]);
}
global $DB;
$DB->update('glpi_configs',['value'=>'es_AR'],['context'=>'core','name'=>'language']);
echo "Instancia local preparada. Usuario: glpi. Credencial en .env local.\n";
