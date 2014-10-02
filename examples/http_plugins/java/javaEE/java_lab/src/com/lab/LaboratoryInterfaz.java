package com.lab;

import java.io.IOException;
import java.io.PrintWriter;

import javax.servlet.ServletContext;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.HttpSession;

import util.InfoReservation;

public abstract class LaboratoryInterfaz extends LabBase{
		
	/**
	 * 
	 */
	private static final long serialVersionUID = 6512142669129224074L;
	private String device;
	
	public LaboratoryInterfaz(){
		device="";
	}
	
	public LaboratoryInterfaz(String s){
		device=" " + s;
	}

	protected void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
		String reservationId = request.getParameter("reservation_id");
		ServletContext context = request.getServletContext();
		//auto reload web page
		response.setIntHeader("Refresh", 2);
		InfoReservation info = (InfoReservation) context.getAttribute(reservationId);
		if (info!= null){
			long now = System.currentTimeMillis();
			if (info.getDeadLine() > now){
				response.setContentType("text/html;charset=UTF-8");
		        PrintWriter out = response.getWriter();
		        device = request.getRequestURI().replace("/java_lab/lab/", "");
		        try {
		            out.println("<html>");
		            out.println("<head>");
		            //auto reload web page, equals to response.setIntHeader("Refresh", 2);
		            //out.println("<meta http-equiv=\"refresh\" content=\"3\">");
		            out.println("</head>");
		            out.println("<body>");
		            out.println("<h2>This would be a widget of the laboratory interface " + device + "!</h2>");
		            out.println("<ul>");
		            out.println("<li>Your username: " + info.getUsername() + "</li>");
		            out.println("<li>Remaining time: " + Long.toString((info.getDeadLine()-now)/1000) + " seconds (refresh to see it change)</li>");
		            out.println("</ul>");
		            out.println("</body>");
		            out.println("</html>");
		        } finally {
		            out.close();
		        }
			}else{
			 	context.removeAttribute(reservationId);
				response.sendRedirect(info.getBack());
			}
		}else
			response.getWriter().write("You must provide a valid reservation identifier");
			
	}

}
