from index_numerorum.visuals import format_elapsed


class TestFormatElapsed:
    def test_milliseconds(self):
        assert format_elapsed(0.5) == "500ms"
        assert format_elapsed(0.001) == "1ms"

    def test_seconds(self):
        assert format_elapsed(1.5) == "1.5s"
        assert format_elapsed(30.0) == "30.0s"

    def test_minutes(self):
        assert format_elapsed(90.0) == "1.5min"
        assert format_elapsed(120.0) == "2.0min"
