package com.lab;

import java.io.IOException;
import java.util.UUID;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;

public class Reserve extends Lab {

	/**
	 * 
	 */
	private static final long serialVersionUID = 1L;
	
	@Override
	protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
		String systemLogin = req.getParameter("system_login");
		String systemPassword = req.getParameter("system_password");
		String username = req.getParameter("username");
		String backUrl = req.getParameter("back_url");
		if (systemLogin.equals(SYSTEM_LOGIN) && systemPassword.equals(SYSTEM_PASSWORD)){
			long now = System.currentTimeMillis();
			String reservationId = UUID.randomUUID().toString();
			HttpSession s = req.getSession();
			s.setAttribute("logged", true);
			s.setAttribute("deadline", now+SESSION_SECONDS);
			s.setAttribute("username", username);
			s.setAttribute("back", backUrl);
			s.setAttribute("reservationId", reservationId);
		}
	}

}

