package com.lab;

import javax.servlet.http.HttpServlet;

public abstract class LabBase extends HttpServlet{

	/**
	 * default serial
	 */
	protected static final long serialVersionUID = 1L;

	protected static final String SYSTEM_LOGIN = "myplugin";

	protected static final String SYSTEM_PASSWORD = "password";

	protected static final int SESSION_SECONDS = 30;

}
