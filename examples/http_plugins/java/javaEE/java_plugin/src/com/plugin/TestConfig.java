package com.plugin;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLConnection;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;







import org.apache.*;
import org.json.simple.JSONObject;

import util.Config;

public class TestConfig extends PluginBase{
	
	protected void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
		String contextId = request.getParameter("context_id");
		if (contextId == null)
			response.getWriter().write("context_id is mandatory");
		else{
			String line;
			String result = "";
			Config config = new Config();
			JSONObject currentPassword = (JSONObject) config.getConfig(contextId);
			String password = "";
			if (currentPassword != null)
				password = currentPassword.get("password").toString();
			URL url = new URL(LAB_URL+"/test/?system_login="+LAB_LOGIN+"&system_password=passwod");
			HttpURLConnection conn =  (HttpURLConnection) url.openConnection();
			conn.setRequestMethod("GET");
			System.out.println(conn.getResponseMessage());
			
			//InputStream is = conn.getInputStream();
			System.out.println("aqui2");
			BufferedReader rd = new BufferedReader(new InputStreamReader(conn.getInputStream()));
	         while ((line = rd.readLine()) != null) {
	        	System.out.println("aqui");
	            result += line;
	         }
	         rd.close();
	         System.out.println(result);
		}
	

	}

}
