@step(u'am logged in as an admin with "([^"]*)"')
def given_i_am_logged_in_as_an_admin_with_group1(step, username_password):
    username, password = username_password.split(":")
    support.create_admin(username, password)

    world.browser.get('http://localhost:5001/login')
    step.given('I fill in "username" with "%s"' % username)
    step.given('I fill in "password" with "%s"' % password)
    step.given('I press "Log in"')
    step.given('I should see "LabManager Admin Dashboard"')
