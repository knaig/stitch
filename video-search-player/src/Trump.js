import React from 'react';

const NewPage = () => {
  return (
    <div style={{ padding: '20px' }}>
      <h1>My New Page</h1>
      <p>This is a simple page created from scratch with some images.</p>
      
      {/* Add Images */}
      <div>
        <img 
          src={`${process.env.PUBLIC_URL}/images/image1.webp`} 
          alt="Description of image 1" 
          style={{ width: '300px', height: 'auto', margin: '10px' }}
        />
        <img 
          src={`${process.env.PUBLIC_URL}/images/image2.jpg`} 
          alt="Description of image 2" 
          style={{ width: '300px', height: 'auto', margin: '10px' }}
        />
      </div>
    </div>
  );
};

export default NewPage;
