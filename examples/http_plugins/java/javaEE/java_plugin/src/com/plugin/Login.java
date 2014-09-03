package com.plugin;

import java.io.IOException;

import javax.servlet.ServletException;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;


public class Login extends PluginBase{
	 /**
	 * 
	 */
	private static final long serialVersionUID = 7126632216119361709L;

	public void doGet(HttpServletRequest request, HttpServletResponse response)
	            throws ServletException, IOException {
		 
		
			 response.getWriter().write("You are logged");
	}

}
