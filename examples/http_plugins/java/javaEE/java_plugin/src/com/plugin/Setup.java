package com.plugin;

import java.io.IOException;
import java.util.HashMap;
import java.util.UUID;

import javax.servlet.ServletContext;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.json.*;

import util.Config;
import util.InfoReservation;


public class Setup extends PluginBase{

	/**
	 * 
	 */
	private static final long serialVersionUID = -8936131953307542923L;
	
	@Override
	protected void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
			String backUrl = request.getParameter("back_url");
			if (backUrl == null)
				response.getWriter().write("Missing back_url");
			else{
				long now = System.currentTimeMillis();
				String reservationId = UUID.randomUUID().toString();
				ServletContext context = request.getServletContext();
				@SuppressWarnings("unchecked")
				HashMap <String, InfoReservation> reservations = (HashMap<String, InfoReservation>) context.getAttribute("reservations");
				if (reservations== null){
					reservations = new HashMap<String,InfoReservation>();
					context.setAttribute("reservations", reservations);
				}
				InfoReservation aux = new InfoReservation(backUrl,now+5*60*1000);
				reservations.put(reservationId, aux);
				JSONObject myJson = new JSONObject();
				myJson.put("url","http://" + request.getServerName()  +":" + request.getServerPort() + request.getContextPath() + "/setup/" + "?reservation_id=" + reservationId);
				response.getWriter().write(myJson.toString());
			}
	}
}
