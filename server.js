const { readFileSync } = require('fs')
const { ApolloServer } = require('apollo-server')
let typeDefs = readFileSync("schema.gql", "utf8")

/**
 * The library produce a schema that isn't 100% to spec.
 * Multiple interfaces are produced like this...
 *
 *   type SuperAdmin implements Node, ISuperAdmin, IAdmin, IUser {...}
 *
 * But the spec dictates it should be
 *   type SuperAdmin implements Node & ISuperAdmin & IAdmin & IUser {...}
 */
function patchTypeDefs(text) {

  let lines = text.split('\n')

  for ( let i = 0; i < lines.length; i++ ) {
    let line = lines[i]
    if ( ~line.indexOf('implements') ) {
      lines[i] = line.replace(/,/g, ' &')
    }
  }

  return lines.join('\n')
}

typeDefs = patchTypeDefs(typeDefs)

console.log(typeDefs)

const server = new ApolloServer({
  typeDefs,
  mocks: true,
  introspection: true,
  playground: true,
});

server.listen().then(({ url }) => {
  console.log(`🚀 Server ready at ${url}`);
});