const { readFileSync } = require('fs')
const { ApolloServer } = require('apollo-server')
const typeDefs = readFileSync("schema.gql", "utf8")

const server = new ApolloServer({
  typeDefs,
  mocks: true,
  introspection: true,
  playground: true,
});

server.listen().then(({ url }) => {
  console.log(`🚀 Server ready at ${url}`);
});