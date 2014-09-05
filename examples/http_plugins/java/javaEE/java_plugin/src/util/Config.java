package util;

import java.io.FileReader;
import java.io.FileWriter;
import java.io.IOException;
import java.net.URL;
import java.nio.file.Path;
import java.nio.file.Paths;

import org.json.simple.JSONObject;
import org.json.simple.parser.JSONParser;
import org.json.simple.parser.ParseException;



public class Config {
	
	private static final String CONFIG_FILE = "plugin_config.json";

	//TODO PROBLEMS WITH PATH IN FILE PLUGIN_CONFIG.JSON
	public void saveConfig(String password, String contextId){
		URL url= getClass().getResource(CONFIG_FILE);
		JSONParser parser = new JSONParser();
		JSONObject json;
		try {
			json = (JSONObject) parser.parse(new FileReader(CONFIG_FILE));
			
		} catch (IOException | ParseException | NullPointerException e) {
			json = new JSONObject();
		}
		JSONObject aux = (JSONObject) json.get(contextId);
		if (aux == null)
			aux = new JSONObject();
		aux.put("password", password);
		json.put(contextId, aux);
		System.out.println(Config.class.getResource(CONFIG_FILE).getPath());
		FileWriter f1;
		try {
			f1 = new FileWriter(CONFIG_FILE);
			Path currentRelativePath = Paths.get("");
			String s = currentRelativePath.toAbsolutePath().toString();
			System.out.println("Current relative path is: " + s);
			//System.out.println(Config.class.getClassLoader());
			f1.write(json.toString());
			f1.close(); 
		} catch (IOException e) {
			// TODO Auto-generated catch block
			e.printStackTrace();
		}
		
		
	}
	
	public JSONObject getConfig(String contextId){
		
		URL url= getClass().getResource(CONFIG_FILE);
		JSONParser parser = new JSONParser();
		JSONObject config;
		
		try {
			JSONObject obj = (JSONObject) parser.parse(new FileReader(CONFIG_FILE));
			config = (JSONObject) obj.get(contextId);
		} catch (IOException | ParseException | NullPointerException e) {
			config = null;
		}
		
		return config;
	}

}
