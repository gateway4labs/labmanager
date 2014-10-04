<html>
<head>
    <meta charset="utf-8"/>
    <title>Slim Framework for PHP 5</title>
    <style>body{margin:0;padding:30px;font:12px/1.5 Helvetica,Arial,Verdana,sans-serif;}h1{margin:0;font-size:48px;font-weight:normal;line-height:48px;}strong{display:inline-block;width:65px;}</style>
</head>
<body>

<h1>Plug-in setup (<a href="<?php echo $this->data['back_url'];?>">back</a>)</h1>
<h2>Configuration Settings</h2>
<p>This is just a demo of how the plug-in can be configured in its own screen. This screen is only accessed by the LabManager administrator to configure the screen. It's not even needed in most scenarios, but sometimes the plug-in could have more than one user (e.g., different LabManagers), and different setups for different LabManager.</p>
<p>This case is simpler, though. You only need to put a password, which by default is password, so the HTTP plug-in can interact with the final laboratory.</p>
<form method="POST" action="<?php echo $this->data['base_url'];?>/setup?reservation_id=<?php echo $this->data['reservation_id'];?>">
    <ul>
        <li>Current password: <i>password</i> <b>CORRECT</b>
        <li>Password: <input type="text" name="password"></input><br>
        <button type="submit">Submit</button>
        </li>
    </ul>
</form>
<p>You can test if the configuration is valid or not using the /test-config method here:</p>
<ul>
    <li><a target="_blank" href="<?php echo $this->data['base_url'];?>/plugin/test_config"><?php echo $this->data['base_url'];?>/plugin/test_config</a>
</ul>
</body>
</html>
