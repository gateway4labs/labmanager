package com.plugin;

import java.io.IOException;
import java.util.HashMap;

import javax.servlet.RequestDispatcher;
import javax.servlet.ServletContext;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import Xbean.TextBean;

public class Setup2 extends PluginBase {
	
	/**
	 * 
	 */
	private static final long serialVersionUID = -2667171259010002771L;
	private TextBean currentPassword;

	@Override
	protected void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
			String reservationId = request.getParameter("reservation_id");
			currentPassword = new TextBean();
			request.setAttribute("currentPassword", currentPassword);
			if (reservationId == null)
				response.getWriter().write("Missing reservation_id");
			else{
				ServletContext context = request.getServletContext();
				@SuppressWarnings("unchecked")
				HashMap <String, InfoReservation> reservations = (HashMap<String, InfoReservation>) context.getAttribute("reservations");
				if (reservations == null || !reservations.containsKey(reservationId))
					response.getWriter().write("Reservation identifier not registered");
				else {
					RequestDispatcher rd =context.getRequestDispatcher("/plugin_form.jsp");
					rd.forward(request,response);
				}
				

			}
	}

}
