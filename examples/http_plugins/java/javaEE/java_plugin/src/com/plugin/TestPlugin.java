package com.plugin;

import java.io.IOException;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.json.JSONObject;

public class TestPlugin extends PluginBase{
	
	private static final long serialVersionUID = -3336994436156876692L;

	protected void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
		String s= "{\"valid\" : \"True\", \"g4l-api-version\" : \"" + VERSION + "\"}";
		
		JSONObject myJson = new JSONObject(s);
		response.getWriter().write(myJson.toString());
	}
}
