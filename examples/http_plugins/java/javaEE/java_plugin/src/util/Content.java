package util;

import java.util.HashMap;
import java.util.Map;

public class Content {
	 private Map<String, Fields> descriptor;

	public HashMap<String, Fields> getDescriptor() {
		return (HashMap<String, Fields>) descriptor;
	}

	public void setDescriptor(Map<String, Fields> descriptor) {
		this.descriptor = descriptor;
	}
}
