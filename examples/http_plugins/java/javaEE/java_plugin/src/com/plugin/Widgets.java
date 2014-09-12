package com.plugin;

import java.io.IOException;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.json.JSONObject;

public class Widgets extends PluginBase{

	private static final long serialVersionUID = -5666612661626536191L;
	
	protected void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
		String laboratoryId = request.getParameter("laboratory_id");
		//This can be retrieved from a database, or by contacting the laboratory
		//in case it manages more than one laboratory.
		if (laboratoryId != null && laboratoryId.equals(LAB_ID)){
			String s= "{\"widgets\": [{\"name\" : \"camera1\",\"description\" : \"Left camera\"},{\"name\" : \"camera2\",\"description\" : \"Right camera\"},]}";
			JSONObject myJson = new JSONObject(s);
			response.getWriter().write(myJson.toString());
		}
		else 
			response.sendError(404,"Lab not found" );
	}


}
