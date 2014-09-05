package util;

public class InfoReservation {
	
	private String backUrl;
	private long expire;
	
	public String getBackUrl() {
		return backUrl;
	}

	public void setBackUrl(String backUrl) {
		this.backUrl = backUrl;
	}

	public long getExpire() {
		return expire;
	}

	public void setExpire(long expire) {
		this.expire = expire;
	}

	public InfoReservation(String backUrl, long expire) {
		super();
		this.backUrl = backUrl;
		this.expire = expire;
	}
	
}
