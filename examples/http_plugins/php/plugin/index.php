<?php

require '../slim/Slim/Slim.php';
require '../slim/Slim/Middleware.php';
require 'middleware/HttpBasicAuth.php';

\Slim\Slim::registerAutoloader();

define ('LAB_ID', 'sample_lab_1');
define ('LAB_URL','http://localhost/lab');

$mc = new Memcached();
$mc->addServer("localhost", 11211);

$app = new \Slim\Slim(array('debug'=> true));
$app->add(new \HttpBasicAuth());

//Plugin routes
$app->get('/', function () {

    echo "Gateway4labs PHP plugin";
});

$app->get('/plugin/', function () {

    echo "Gateway4labs PHP plugin";
});


// Static methods (e.g., plug-in capabilities or version)

$app->get('/plugin/test_plugin', function () use ($app) {

    $context_id = $app->request->get('context_id');
    $jsonResponse = array('valid' => true, 'g4l-api-version' => 1);
    $app->contentType('application/json');
    echo json_encode($jsonResponse);
});

$app->get('/plugin/capabilities', function () use ($app) {

    $app->contentType('application/json');
    $jsonResponse = array('capabilities' => array('widget'));
    echo json_encode($jsonResponse);
});

$app->get('/plugin/labs', function () use ($app) {
//Should be retrieved from a database or from the remote lab system

    $jsonResponse = array(
        'labs' => array(
            array(
                'laboratory_id' => 'sample_lab_1',
                'name' => 'Sample Laboratory',
                'description' => 'This is an example of laboratory',
                'autoload' => false),
            array(
            'laboratory_id' => 'sample lab 2',
            'name' => 'Sample Laboratory 2',
            'description' => 'This is an example of laboratory',
            'autoload' => false)

        ),

    );
    $app->contentType('application/json');
    echo json_encode($jsonResponse);
});
//Optional support for widgets
$app->get('/plugin/widgets', function () use($app) {

    $lab_id = $app->request->get('laboratory_id');
    if ($lab_id != LAB_ID){
        echo 'Lab Not found';
        }
    else{
        $jsonResponse = array(
            'widgets' => array(
                array(
                    'name' => 'camera1',
                    'description' => 'Left Camera of the lab'),
                array(
                    'name' => 'camera2',
                    'description' => 'Right Camera')
            ),
        );
    $app->contentType('application/json');
    echo json_encode($jsonResponse);
    }
});

$app->get('/plugin/widget', function () use($app) {
//This method could also query a database to retrieve the widget given a widget_name
    $reservation_id = $app->request->headers('X-G4L-reservation-id');
    $widget_name = $app->request->get('widget_name');

    if ( $widget_name == 'camera1'){
        $jsonResponse = array('url' => 'http://google.com');
        $app->contentType('application/json');
        echo json_encode($jsonResponse);
    }
    elseif ($widget_name == 'camera2'){
        $jsonResponse = array('url' => LAB_URL.'/camera2/?reservation_id='.$reservation_id);
        $app->contentType('application/json');
        echo json_encode($jsonResponse);
    }
    else{
        echo 'Widget not found';
    }
});

//Methods that actually connect to the lab

$app->get('/plugin/test_config', function () use($app) {
    $context_id = $app->request->get('context_id');
//This method should contact the lab and return 'valid': true if successful
// or 'valid': false
//    'error-message': message
//if false
    $valid = true;
    if ($valid == true){
        $jsonResponse = array('valid' => true);
        $app->contentType('application/json');
        echo json_encode($jsonResponse);
    }
    else{
        $jsonResponse = array('valid' => false,
                              'error-message' => 'error message goes here');
        $app->contentType('application/json');
        echo json_encode($jsonResponse);
    }

});

$app->map('/plugin/reserve', function () use($app) {
//This method should contact the lab to create a reservation
    $context_id = $app->request->get('context_id');
    $request = $app->request->getBody();
    $JsonRequest = json_decode($request, true);

    if ($JsonRequest == null){
        $app->response->setStatus(400);
        echo 'Invalid JSON document';

    }
    else{
        $laboratory_id = $JsonRequest['laboratory_id'];
        $username = $JsonRequest['username'];
        //$institution = $JsonRequest['institution'];

        //$general_configuration_str = $JsonRequest['general_configuration_str'];
        //$particular_configurations = $JsonRequest['particular_configurations'];
        //$request_payload = $JsonRequest['request_payload'];
        //$user_properties = $JsonRequest['user_properties'];

//Json responses "load_url" and "reservation_id" should be retrieved by querying the lab

        $jsonResponse = array('load_url' => 'http://your.load.url',
                              'reservation_id' => 'reservation ID');
        $app->contentType('application/json');
        echo json_encode($jsonResponse);
        //echo json_encode($laboratory_id);

    }
})->via('GET', 'POST');

//
$app->get('/plugin/setup', function() use($app, $mc){

    $context_id = $app->request->get('context_id');
    $back_url = $app->request->get('back_url');
    $date = date('Y-m-d H:i:s');
    $reservation_id = md5($date);
    $mc->set("reservations", array($reservation_id => array(
        'reservation_id' =>  $reservation_id,
        'expires' => $date,
        'back_url' => $back_url
)));
    $jsonResponse = array('url' => $app->request()->getUrl().'/setup?reservation_id='.$reservation_id);
    $app->contentType('application/json');
    echo json_encode($jsonResponse);

});

$app->map('/setup', function() use($app, $mc){

    $context_id = $app->request->get('context_id');
    $password = $app->request()->params('password');
    $reservation_id = $app->request->get('reservation_id');
    $reservations = $mc->get("reservations");
    $app->view()->setData(array('back_url'=> $reservations[$reservation_id]['back_url'],
                                'base_url' => $app->request()->getUrl(),
                                'reservation_id'=> $reservation_id,
                                'password' => $password

    ));
    $app->render('plugin_form.php');

})->via('GET','POST');


$app->run();
