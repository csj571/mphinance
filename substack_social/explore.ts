import { SubstackClient } from 'substack-api';

const sid = "s%3AbOEIouthsRC1PWBVi8Jl07qP4-pMjLiz.8aqscWSVtI65wqmEAsGMfJpWSxHXyaIJgcYadK%2BoG7k";

async function main() {
  const client = new SubstackClient({
    token: sid,
    publicationUrl: 'mphinance.substack.com',
  });

  const isConnected = await client.testConnectivity();
  console.log("Connected:", isConnected);

  if (isConnected) {
    const profile = await client.ownProfile();
    console.log("Profile Name:", profile.name);
    console.log("Profile keys:", Object.keys(profile));
    
    // Check if profile has access to following or feed
    console.log("Type of profile:", profile.constructor.name);
    console.log("Profile methods:", Object.getOwnPropertyNames(Object.getPrototypeOf(profile)));
    
    // Let's try to get profile's following or something
  }
}

main().catch(console.error);
