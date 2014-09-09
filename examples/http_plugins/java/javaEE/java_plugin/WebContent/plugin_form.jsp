<%@page contentType="text/html"%>
<%@page pageEncoding="UTF-8"%>
<html>
<head>
	<jsp:useBean id="currentPassword" scope="session" class="Xbean.TextBean" />
</head>
<body>
	<h1>Plug-in setup (<a href="">back</a>)</h1>
	
	<p>This is just a demo of how the plug-in can be configured in its own screen. This screen is only accessed by the LabManager administrator to configure the screen. It's not even needed in most scenarios, but sometimes the plug-in could have more than one user (e.g., different LabManagers), and different setups for different LabManager.</p>
	
	<p>This case is simpler, though. You only need to put a password, which by default is password, so the HTTP plug-in can interact with the final laboratory.</p>
	
	<form method="POST" action="">
	    <ul>
	        <li>Current password: <i><jsp:getProperty name="currentPassword" property="text" /> </i></li>
	        <li>Password: <input type="text" name="password"></input><br>
	        <button type="submit">Submit</button>
	        </li>
	    </ul>
	</form>
	
	<p>You can test if the configuration is valid or not using the /test-config method here:</p>
	
	<ul>
	    <li><a href=""></a>
	</ul>

</body>

</html>

