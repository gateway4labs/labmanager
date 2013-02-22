Feature: Launching LTI Experiments
  In order to launch a lab from a LTI supported LMS
  As a student
  I want reserve and launch a lab

  Scenario: Accessing the list of available laboratories to launch
    Given An OAuth LMS with public key "shared" and private key "secret"
    And an laboratory named "dancing-robots-under-the-rain" exists
    And LMS with public key "shared" has permission on laboratory "dancing-robots-under-the-rain"
    And I come from course "fun-learning"
    And Course "fun-learning" has permission "granted" to use laboratory "dancing-robots-under-the-rain"
    When I launch the LTI tool
    Then I should see "dancing-robots-under-the-rain" at the granted laboratories list


  Scenario: Launching a laboratory
    Given I can access "dancing-robots" from the course "fun-learning"
    And I am at the available laboratory list
    When I select "dancing-robots" from the granted laboratories list
    And I launch the laboratory
    Then "dancing-robots" should be reserved
