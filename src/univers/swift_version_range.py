import attr

from univers.version_constraint import VersionConstraint
from univers.version_range import VersionRange
from univers.versions import SwiftVersion


@attr.s(auto_attribs=True, frozen=True)
class SwiftVersionRange(VersionRange):
    expression: str
    scheme: str = "swift"
    version_class: type = SwiftVersion
    constraints: list = attr.ib(init=False)

    def __attrs_post_init__(self):
        object.__setattr__(self, "constraints", self.parse(self.expression))

    @staticmethod
    def parse(expression):
        constraints = []
        # Remove quotes for parsing.
        expression = expression.replace('"', "").strip()

        # Handle different range types.
        if "..<" in expression:
            parts = expression.split("..<")
            if len(parts) == 2:
                lower = SwiftVersion(parts[0].strip())
                upper = SwiftVersion(parts[1].strip())
                constraints.append(VersionConstraint(comparator=">=", version=lower))
                constraints.append(VersionConstraint(comparator="<", version=upper))
        elif "..." in expression:
            parts = expression.split("...")
            if len(parts) == 2:
                lower = SwiftVersion(parts[0].strip())
                upper = SwiftVersion(parts[1].strip())
                constraints.append(VersionConstraint(comparator=">=", version=lower))
                constraints.append(VersionConstraint(comparator="<=", version=upper))
        else:
            # Handle other cases such as 'exact:' and 'from:' prefixes.
            if "exact:" in expression:
                version = SwiftVersion(expression.split("exact:")[1].strip())
                constraints.append(VersionConstraint(comparator="=", version=version))
            elif "from:" in expression:
                version = SwiftVersion(expression.split("from:")[1].strip())
                next_major_version = version.next_major()
                constraints.append(VersionConstraint(comparator=">=", version=version))
                constraints.append(VersionConstraint(comparator="<", version=next_major_version))
            else:
                # Handle a single version without any prefix.
                version = SwiftVersion(expression)
                constraints.append(VersionConstraint(comparator="=", version=version))

        return constraints

    def __str__(self):
        return f"vers:swift/{'|'.join([c.to_string() for c in self.constraints])}"
