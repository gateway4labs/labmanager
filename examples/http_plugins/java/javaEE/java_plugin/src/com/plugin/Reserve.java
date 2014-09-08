package com.plugin;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;
import java.util.HashMap;

import javax.servlet.ServletContext;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;


import org.json.simple.*;

import util.Config;
import util.InfoReservation;

public class Reserve extends PluginBase {
	
	private String username = "username not provided";
	private String backUrl = "https://github.com/gateway4labs/";
	/**
	 * 
	 */
	private static final long serialVersionUID = -7796384281812019095L;

	protected void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
		String contextId = request.getParameter("context_id");
		
		if (contextId == null)
			response.getWriter().write("context_id is mandatory");
		else {
			String line;
			String result = "";
			Config config = new Config();
			JSONObject currentPassword = (JSONObject) config.getConfig(contextId);
			String reservationUrl = LAB_URL + "/reserve/?system_login=" + LAB_LOGIN + "&system_password=" + currentPassword.get("password").toString() + 
					"&username=tusmuertos" + "&back_url=" + backUrl;
			System.out.println(reservationUrl);
			URL url = new URL(reservationUrl);
			HttpURLConnection conn =  (HttpURLConnection) url.openConnection();
			conn.setRequestMethod("GET");
			
			BufferedReader rd = new BufferedReader(new InputStreamReader(conn.getInputStream(),"UTF-8"));
	        while ((line = rd.readLine()) != null) {
	            result += line;
	        }
	        rd.close();
	        JSONObject resultJson = (JSONObject) JSONValue.parse(result);
	        System.out.println(result);
	        System.out.println(resultJson);
	        response.getWriter().write(resultJson.toString());

     
		
		}
	}

}
