package com.lab;

import java.io.IOException;

import javax.servlet.ServletException;
import javax.servlet.annotation.WebServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;



import org.json.JSONObject;


@WebServlet(name="TestServlet", urlPatterns={"/test/"}) 
public class Test extends LabBase {

	/**
	 * 
	 */
	private static final long serialVersionUID = 720438497328397854L;

	protected void doGet(HttpServletRequest request, HttpServletResponse response) throws ServletException, IOException {
			String systemLogin = request.getParameter("system_login");
			String systemPassword = request.getParameter("system_password");
			JSONObject myJson = new JSONObject();
			if (systemLogin != null && systemPassword != null){
				if (systemLogin.equals(SYSTEM_LOGIN) && systemPassword.equals(SYSTEM_PASSWORD)){
					response.getWriter().write("ok");
				}		
			}else{ 
				myJson.put("Error", "invalid credentials'");
				response.getWriter().write(myJson.toString());
			}
		}
}
	
	


