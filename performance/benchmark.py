"""Simple benchmark for marshmallow serialization of a moderately complex object.

Uses the `timeit` module to benchmark serializing an object through marshmallow.
"""

# ruff: noqa: A002, T201
import argparse
import cProfile
import datetime
import gc
import timeit

from marshmallow import Schema, ValidationError, fields, post_dump


# Custom validator
def must_not_be_blank(data):
    if not data:
        raise ValidationError("Data not provided.")


class AuthorSchema(Schema):
    id = fields.Int(dump_only=True)
    first = fields.Str()
    last = fields.Str()
    book_count = fields.Float()
    age = fields.Float()
    address = fields.Str()
    full_name = fields.Method("get_full_name")

    def get_full_name(self, author):
        return f"{author.last}, {author.first}"


class QuoteSchema(Schema):
    id = fields.Int(dump_only=True)
    author = fields.Nested(AuthorSchema, validate=must_not_be_blank)
    content = fields.Str(required=True, validate=must_not_be_blank)
    posted_at = fields.DateTime(dump_only=True)
    book_name = fields.Str()
    page_number = fields.Float()
    line_number = fields.Float()
    col_number = fields.Float()

    @post_dump
    def add_full_name(self, data, **kwargs):
        data["author_full"] = "{}, {}".format(
            data["author"]["last"], data["author"]["first"]
        )
        return data


class Author:
    def __init__(self, id, first, last, book_count, age, address):
        self.id = id
        self.first = first
        self.last = last
        self.book_count = book_count
        self.age = age
        self.address = address


class Quote:
    def __init__(
        self,
        id,
        author,
        content,
        posted_at,
        book_name,
        page_number,
        line_number,
        col_number,
    ):
        self.id = id
        self.author = author
        self.content = content
        self.posted_at = posted_at
        self.book_name = book_name
        self.page_number = page_number
        self.line_number = line_number
        self.col_number = col_number


def run_timeit(quotes, iterations, repeat, *, profile=False):
    quotes_schema = QuoteSchema(many=True)
    if profile:
        profile = cProfile.Profile()
        profile.enable()

    gc.collect()
    best = min(
        timeit.repeat(
            lambda: quotes_schema.dump(quotes),
            "gc.enable()",
            number=iterations,
            repeat=repeat,
        )
    )
    if profile:
        profile.disable()
        profile.dump_stats("marshmallow.pprof")

    return best * 1e6 / iterations / len(quotes)


def main():
    parser = argparse.ArgumentParser(description="Runs a benchmark of Marshmallow.")
    parser.add_argument(
        "--iterations",
        type=int,
        default=1000,
        help="Number of iterations to run per test.",
    )
    parser.add_argument(
        "--repeat",
        type=int,
        default=5,
        help="Number of times to repeat the performance test.  The minimum will "
        "be used.",
    )
    parser.add_argument(
        "--object-count", type=int, default=20, help="Number of objects to dump."
    )
    parser.add_argument(
        "--profile",
        action="store_true",
        help="Whether or not to profile marshmallow while running the benchmark.",
    )
    args = parser.parse_args()

    quotes = [
        Quote(
            i,
            Author(i, "Foo", "Bar", 42, 66, "123 Fake St"),
            "Hello World",
            datetime.datetime(2019, 7, 4, tzinfo=datetime.timezone.utc),
            "The World",
            34,
            3,
            70,
        )
        for i in range(args.object_count)
    ]

    print(
        f"Benchmark Result: {run_timeit(quotes, args.iterations, args.repeat, profile=args.profile):.2f} usec/dump"
    )


if __name__ == "__main__":
    main()
