package com.plugin;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.json.JSONException;
import org.json.JSONObject;

import util.Config;

public class TestConfig extends PluginBase{
	
	private static final long serialVersionUID = 6703669684532242222L;

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
			URL url = new URL(LAB_URL+"/test/?system_login="+LAB_LOGIN+"&system_password="+password);
			HttpURLConnection conn =  (HttpURLConnection) url.openConnection();
			conn.setRequestMethod("GET");
			
			BufferedReader rd = new BufferedReader(new InputStreamReader(conn.getInputStream()));
	        while ((line = rd.readLine()) != null) {
	            result += line;
	        }
	        rd.close();
	        System.out.println(result);
     		JSONObject json = new JSONObject();
	        if (result.equals("ok")){
	        	json.put("valid", true);
	        }
	        else{
	        	json.put("valid", false);
		        try{
		        	JSONObject resultJson = new JSONObject(result);
		        	json.put("error-messages", resultJson.getString("Error"));
		        } catch (JSONException e ){
		        	json.put("error-messages", "Error and laboratory did not provide a proper JSON error message.");
		        }
	        }
	        response.getWriter().write(json.toString());
         }	
	}

}
