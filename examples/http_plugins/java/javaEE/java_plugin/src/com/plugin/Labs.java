package com.plugin;

import java.io.IOException;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.json.JSONObject;

public class Labs extends PluginBase {
	
	private static final long serialVersionUID = 1880799586566000915L;

	//This can be retrieved from a database, or by contacting the laboratory
    // in case it manages more than one laboratory.
	protected void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
		String s= "{\"labs\": [{\"name\" : \"Sample laboratory\",\"description\" : \"This is an example of laboratory\",\"autoload\" : \"False\",\"laboratory_id\" :" + LAB_ID + ",}]}";
		
		JSONObject myJson = new JSONObject(s);
		response.getWriter().write(myJson.toString());
	}
	

}
