package com.plugin;

import java.io.IOException;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.json.JSONObject;

public class Capabilities extends PluginBase {
	
	private static final long serialVersionUID = -5103401959967586765L;

	protected void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
		String s= "{\"capabilities\" : [\"widget\"]}";
		JSONObject myJson = new JSONObject(s);
		response.getWriter().write(myJson.toString());
	}

}
