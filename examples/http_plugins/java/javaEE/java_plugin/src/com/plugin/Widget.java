package com.plugin;

import java.io.IOException;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.json.JSONObject;

public class Widget extends PluginBase{

	private static final long serialVersionUID = 1383750801258709775L;
	
	protected void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
		String widgetName = request.getParameter("widget_name");
		String s;
		String reservationId = request.getHeader("X-G4L-reservation-id");
		if (widgetName != null){
			if (widgetName.equals("camera1")){
					s = "{\"url\" : \"" + LAB_URL + "/lab/camera1?reservation_id=" + reservationId + "\"}";
					JSONObject myJson = new JSONObject(s);
					response.getWriter().write(myJson.toString());
					return;
			}
			else{
				if (widgetName.equals("camera2")){
						s = "{\"url\" : \"" + LAB_URL + "/lab/camera2?reservation_id=" + reservationId + "\"}";
						JSONObject myJson = new JSONObject(s);
						response.getWriter().write(myJson.toString());
						return;
				}
			}
		}
		response.sendError(404,"Lab not found" );
	}

}
