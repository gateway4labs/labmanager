Feature: Adding a LMS
  In order to allow students from LMS to use the labs
  As a labmanager administrator
  I want add a new LMS to the system

  Scenario: Looking at LMS on the homepage
    Given I am logged in as an admin with "labmanager_admin:password"
    And an OAuth LMS with name "test lms name" and url "http://example.com"
    When I visit the LMS list page
    Then I should see "test lms name"
    And I should see "http://example.com"

  Scenario: Adding an OAuth LMS with correct credentials
    Given I am logged in as an admin with "labmanager_admin:password"
    When I add an oauth LMS with name "test" and url "http://example.com"
    And I visit the LMS list page
    Then I should see "test"
    And I should see "http://example.com"

  Scenario: Adding a basic auth LMS with correct credentials
    Given I am logged in as an admin with "labmanager_admin:password"
    When I add an basic auth LMS with name "basic auth" and url "http://example.com"
    And I visit the LMS list page
    Then I should see "basic auth"
    And I should see "http://example.com"
