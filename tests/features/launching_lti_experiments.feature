Feature: Launching LTI Experiments
  In order to launch a lab from a LTI supported LMS
  As a student
  I want reserve and launch a lab

  Scenario: Reserving a lab
    Given An OAuth LMS with public key "shared" and private key "secret"
    And an experiment named "dancing-robots-under-the-rain" exists
    And LMS "shared" has permission to access "dancing-robots-under-the-rain"
    When I reserve "dancing-robots-under-the-rain" as "shared:secret"
    Then the experiment should be reserved
