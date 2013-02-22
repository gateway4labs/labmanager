Feature: Launching LTI Experiments
  In order to launch a lab from a LTI supported LMS
  As a student
  I want reserve and launch a lab

  Scenario: Reserving a lab
    Given An OAuth LMS with public key "shared" and private key "secret"
    And an laboratory named "dancing-robots-under-the-rain" exists
    And LMS with public key "shared" has permission on laboratory "dancing-robots-under-the-rain"
    And the student comes from Course "fun-learning"
    And Course "fun-learning" has permission granted to use laboratory "dancing-robots-under-the-rain" 
    When the student selects "dancing-robots-under-the-rain" from the laboratories list
    Then the experiment should be reserved
