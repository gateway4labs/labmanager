Feature: Authenticate through lti
  In order to gain access to the labs
  As a LMS user
  I want authenticate using the LTI standard

  Scenario: Authenticate with valid credentials
    Given a LMS with 'shared' public and 'secret' secret keys
    When I authenticate with 'shared' and 'signature'
    Then I should be authenticated
    Then I should get a "200" http code

  Scenario: Authenticate with invalid shared key
    Given no LMS
    When I authenticate with 'non-existent-shared' and 'signature'
    Then I should get a "412" http code

  Scenario: Authenticate with invalid signature
    Given a LMS with 'shared' public and 'secret' secret keys
    When I authenticate with 'shared' and 'wrong-signature'
    Then I should get a "403" http code