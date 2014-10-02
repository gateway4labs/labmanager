package util;

public class InfoReservation {

	private long deadLine;
	private String back;
	private String username;
	
	public InfoReservation() {
	}
	
	public InfoReservation(long deadLine, String back, String username) {
		this.deadLine = deadLine;
		this.back = back;
		this.username = username;
	}
	
	public long getDeadLine() {
		return deadLine;
	}
	
	public void setDeadLine(long deadLine) {
		this.deadLine = deadLine;
	}
	
	public String getBack() {
		return back;
	}
	
	public void setBack(String back) {
		this.back = back;
	}
	
	public String getUsername() {
		return username;
	}
	
	public void setUsername(String username) {
		this.username = username;
	}
	
}
