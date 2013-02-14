Feature: Adding a LMS
  In order to allow students from LMS to use the labs
  As a labmanager administrator
  I want add a new LMS to the system

  Scenario: Looking at LMS on the homepage
    Given I am logged in as an admin with "admin:password"
    And an OAuth LMS with name "test lms name" and url "http://example.com"
    When I visit the LMS list page
    Then I should see "test lms name"
    And I should see "http://example.com"

  Scenario: Adding a LMS with correct credentials
    Given I am logged in as an admin with "admin:password"
    When I add an oauth LMS with name "test" and url "http://example.com"
    And I visit the LMS list page
    Then I should see "test"
    And I should see "http://example.com"