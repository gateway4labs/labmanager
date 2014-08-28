package com.lab;

import java.io.IOException;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;

@WebServlet(name="LabServlet", urlPatterns={"/lab/"}) 
public class Lab extends LabBase{
	
	/**
	 * 
	 */
	private static final long serialVersionUID = -5448439588609644067L;

	@Override
	protected void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
		String reservationId = request.getParameter("reservation_id");
		HttpSession s = request.getSession();
		if (reservationId.equals(s.getAttribute("reservationId"))){
			response.sendRedirect((String) s.getAttribute("back"));
		}
	}
}
