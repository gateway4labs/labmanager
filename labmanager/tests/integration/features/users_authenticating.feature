Feature: Admin Users Authenticating
  In order to manage the Lab Manager application
  As an admin user
  I want to be able to login and logout

  Scenario: Logging in with right credentials
    Given an admin user with "username:password"
    When I login with "username:password"
    Then I should be logged in

  Scenario: Logging in with wrong credentials
    Given there are no admins
    When I login with "username:password"
    Then I should not be logged in