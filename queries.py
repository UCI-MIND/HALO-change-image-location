from gql import gql

# The GraphQL workbench on the HALO Link website uses doubled backslashes for its query arguments.

query_imageByPk = gql("""
query imageByPk ($pk: Int!)
{
  imageByPk(pk: $pk) {
    id
  }
}
""")
# Example variables: {"pk": 99}
# pk should be an integer

query_imagesByLocation = gql("""
query imagesByLocation ($location: String!)
{
  imagesByLocation(location: $location) {
    pk
    id
    location
  }
}
""")
# Example variables: {"location": "\\\\1.2.3.4\\lab_bowser\\scans\\Scan001.scn"}
# location should be the current path that HALO recognizes (which may not actually exist)

mutation_changeImageLocation = gql("""
mutation changeImageLocation ($input: ChangeImageLocationInput!)
{
  changeImageLocation(input: $input) {
    mutated {
      node {
        pk
        location
      }
    }
    failed {
      error
      input
    }
  }
}
""")
# Example variables: {
#                   "input": {
#                     "imageId": "SW1hZ2U6MQ==",
#                     "newLocation": r"\\1.2.3.4\lab_bowser\waluigi\updated_folder\Scan001.scn",
#                   }
#                 }
# imageId should NOT be a pk! Get imageId from either of the queries above
# newLocation is determined by researchers and how their storage server is organized
