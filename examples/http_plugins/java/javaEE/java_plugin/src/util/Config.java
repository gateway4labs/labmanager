package util;


import java.io.BufferedReader;
import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.net.URL;

import org.json.JSONException;
import org.json.JSONObject;


public class Config {
	
	private static final String CONFIG_FILE = "plugin_config.json";

	//TODO PROBLEMS WITH PATH IN FILE PLUGIN_CONFIG.JSON
	public void saveConfig(String password, String contextId){
		URL url= getClass().getResource(CONFIG_FILE);
		String line="";
		String result="";
		JSONObject json = null;
		JSONObject aux;
		try {
			BufferedReader rd = new BufferedReader( new FileReader (CONFIG_FILE));
	        while ((line = rd.readLine()) != null)
	            result += line;
	        rd.close();
	        json = new JSONObject(result);
	        aux = (JSONObject) json.get(contextId);
			aux.put("password", password);
			json.put(contextId, aux);
		} catch ( JSONException e) {
			json = new JSONObject();
			aux = new JSONObject();
			aux.put("password", password);
			json.put(contextId, aux);
		}
		catch (IOException e) {
			e.printStackTrace();
		}
		
		FileWriter f1;
		try {
			f1 = new FileWriter(CONFIG_FILE);
			f1.write(json.toString());
			f1.close(); 
		} catch (IOException e) {
			e.printStackTrace();
		}	
	}
	
	public JSONObject getConfig(String contextId){
		
		URL url= getClass().getResource(CONFIG_FILE);
		String line="";
		String result="";
		JSONObject config;
		try {
			BufferedReader rd = new BufferedReader( new FileReader (CONFIG_FILE));
	        while ((line = rd.readLine()) != null)
	            result += line;
	        rd.close();
	        config = new JSONObject(result);
			config = config.getJSONObject(contextId);
		} catch (IOException | NullPointerException | JSONException e) {
			config = null;
		}
			
		return config;
	}
	
}
