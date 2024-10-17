from utils import scrub_email_addresses, scrub_names


def test_scrub_email():
    assert scrub_email_addresses(
        """
    My email is 'adam@example.com'
    """
    ) == (
        """
    My email is '<email>'
    """
    )


def test_scrub_names():
    assert scrub_names(
        """
    Hi Dom

    Thanks for the help with this.

    Best,

    John
    """
    ) == (
        """
    Hi <name>

    Thanks for the help with this.

    Best,

    <name>

    """
    )
