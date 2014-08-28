package com.lab;

import javax.servlet.http.HttpServlet;

public abstract class LabBase extends HttpServlet{

	/**
	 * default serial
	 */
	private static final long serialVersionUID = 1L;

	public static final String SYSTEM_LOGIN = "myplugin";

	public static final String SYSTEM_PASSWORD = "password";

	public static final int SESSION_SECONDS = 30;

}
