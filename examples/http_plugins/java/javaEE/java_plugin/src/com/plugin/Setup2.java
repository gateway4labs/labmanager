package com.plugin;

import java.io.IOException;
import java.util.HashMap;

import javax.servlet.RequestDispatcher;
import javax.servlet.ServletContext;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

import org.json.simple.JSONObject;

import util.Config;
import util.InfoReservation;
import Xbean.TextBean;

public class Setup2 extends PluginBase {
	
	/**
	 * 
	 */
	private static final long serialVersionUID = -2667171259010002771L;
	private TextBean currentPasswordBean;
	private TextBean currentPasswordCorrectBean;
	private TextBean urlBackBean;
	private TextBean urlTestBean;

	@Override
	protected void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
			String reservationId = request.getParameter("reservation_id");
			String contextId = request.getParameter("context_id");
			
			if (reservationId == null)
				response.getWriter().write("Missing reservation_id");
			else{
				if (contextId == null)
					response.getWriter().write("context_id is mandatory");
				else {
					ServletContext context = request.getServletContext();
					@SuppressWarnings("unchecked")
					HashMap <String, InfoReservation> reservations = (HashMap<String, InfoReservation>) context.getAttribute("reservations");
					if (reservations == null || !reservations.containsKey(reservationId))
						response.getWriter().write("Reservation identifier not registered");
					else {
						Config config = new Config();
						JSONObject currentPassword = (JSONObject) config.getConfig(contextId);
						currentPasswordBean = new TextBean();
						if (currentPassword != null)
							currentPasswordBean.setText(currentPassword.get("password").toString());
						request.setAttribute("currentPassword", currentPasswordBean);
						boolean currentPasswordCorrect;
						if (currentPassword !=null)
							currentPasswordCorrect = currentPassword.get("password").equals(PLUGIN_PASSWORD);
						else
							currentPasswordCorrect = false;
						currentPasswordCorrectBean = new TextBean();
						if (currentPasswordCorrect)
							currentPasswordCorrectBean.setText("CORRECT");
						else
							currentPasswordCorrectBean.setText("INCORRECT");
						request.setAttribute("currentPasswordCorrect", currentPasswordCorrectBean);
						InfoReservation info = reservations.get(reservationId);
						urlBackBean = new TextBean();
						urlBackBean.setText(info.getBackUrl());
						request.setAttribute("urlBack", urlBackBean);
						urlTestBean = new TextBean();
						urlTestBean.setText("http://" + request.getServerName()  +":" + request.getServerPort() + request.getContextPath() + "/test_config?context_id=" + contextId);
						request.setAttribute("urlTest", urlTestBean);
						RequestDispatcher rd =context.getRequestDispatcher("/plugin_form.jsp");
						rd.forward(request,response);
					}
				}
			}
	}
	
	protected void doPost(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
		String password = request.getParameter("password");
		String contextId = request.getParameter("context_id");
		Config config = new Config();
		config.saveConfig(password, contextId);
		response.sendRedirect(request.getRequestURL().toString()+"?"+request.getQueryString());
		return;
	}
}

