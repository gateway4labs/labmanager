Feature: Adding a LMS
  In order to allow students from LMS to use the labs
  As a labmanager administrator
  I want add a new LMS to the system

  Scenario: Looking at LMS on the homepage
    Given I am logged in as an admin with 'user:password'
    And an OAuth LMS
    When I visit the LMS list page
    Then the LMS list should have:
      | name | url                |
      | test | http://example.com |

  Scenario: Adding a LMS with correct credentials
    Given I am logged in as an admin with 'user:password'
    When I add an oauth LMS with name 'test' and url 'http://example.com'
    And I visit the LMS list page
    Then the LMS list should have:
      | name | url                |
      | test | http://example.com |
  
  
  
