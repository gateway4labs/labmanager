package com.plugin;

import javax.servlet.http.HttpServlet;

public abstract class PluginBase extends HttpServlet {

	/**
	 * 
	 */
	private static final long serialVersionUID = 1784707071462582503L;

	protected static final int VERSION = 1;

	protected static final String PLUGIN_USERNAME = "labmanager";

	protected static final String PLUGIN_PASSWORD = "password";

	protected static final String LAB_ID = "samplelab";

	protected static final String LAB_URL = "http://localhost:8080/java_lab";

	protected static final String LAB_LOGIN = "myplugin";
}
